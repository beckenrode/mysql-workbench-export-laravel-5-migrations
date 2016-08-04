# -*- coding: utf-8 -*-
# MySQL Workbench module
# A MySQL Workbench plugin which exports a Model to Laravel 5 Migrations
# Written in MySQL Workbench 6.3.6

import re
import cStringIO

import grt
import mforms
import datetime

from grt.modules import Workbench
from wb import DefineModule, wbinputs
from workbench.ui import WizardForm, WizardPage
from mforms import newButton, newCodeEditor, FileChooser

ModuleInfo = DefineModule(name='GenerateLaravel5Migration',
                          author='Brandon Eckenrode',
                          version='0.1.2')

@ModuleInfo.plugin('wb.util.generateLaravel5Migration',
                   caption='Export Laravel 5 Migration',
                   input=[wbinputs.currentCatalog()],
                   groups=['Catalog/Utilities', 'Menu/Catalog'])
@ModuleInfo.export(grt.INT, grt.classes.db_Catalog)

def generateLaravel5Migration(cat):
    def export_schema(out, schema, is_main_schema):
        if len(schema.tables) == 0:
            return

        foreign_keys = {}
        migration_tables = []
        global migrations

        for tbl in sorted(schema.tables, key=lambda table: table.name):
            migration_tables.append(tbl.name)
            migrations[tbl.name] = []
            migrations[tbl.name].append('<?php\n')
            migrations[tbl.name].append('\n')
            migrations[tbl.name].append('use Illuminate\Database\Schema\Blueprint;\n')
            migrations[tbl.name].append('use Illuminate\Database\Migrations\Migration;\n')
            migrations[tbl.name].append('\n')
            components = tbl.name.split('_')
            migrations[tbl.name].append('class Create%sTable extends Migration\n' % ("".join(x.title() for x in components[0:])))
            migrations[tbl.name].append('{\n')
            migrations[tbl.name].append('    /**\n')
            migrations[tbl.name].append('     * Run the migrations.\n')
            migrations[tbl.name].append('     *\n')
            migrations[tbl.name].append('     * @return void\n')
            migrations[tbl.name].append('     */\n')
            migrations[tbl.name].append('    public function up()\n')
            migrations[tbl.name].append('    {\n')
            migrations[tbl.name].append('        Schema::create(\'%s\', function (Blueprint $table) {\n' % (tbl.name))

            created_at = created_at_nullable = updated_at = updated_at_nullable = deleted_at = timestamps = timestamps_nullable = False

            for col in tbl.columns:
                if col.name == 'created_at':
                    created_at = True
                    if col.isNotNull != 1:
                        created_at_nullable = True
                elif col.name == 'updated_at':
                    updated_at = True
                    if col.isNotNull != 1:
                        updated_at_nullable = True

            if created_at is True and updated_at is True and created_at_nullable is True and updated_at_nullable is True:
                timestamps_nullable = True
            elif created_at is True and updated_at is True:
                timestamps = True

            for col in tbl.columns:
                if (col.name == 'created_at' or col.name == 'updated_at') and (timestamps is True or timestamps_nullable is True):
                    continue
                if col.name == 'deleted_at':
                    deleted_at = True
                    continue

                if col.simpleType:
                    col_type = col.simpleType.name
                    col_flags = col.simpleType.flags
                else:
                    col_type = col.userType.name
                    col_flags = col.flags

                primary_key = [i for i in tbl.indices if i.isPrimary == 1]
                primary_key = primary_key[0] if len(primary_key) > 0 else None

                pk_column = None
                if primary_key and len(primary_key.columns) == 1:
                    pk_column = primary_key.columns[0].referencedColumn

                if col == pk_column:
                    if col_type == 'BIGINT':
                        col_type = 'BIGINCREMENTS'
                    else:
                        col_type = 'INCREMENTS'

                col_data = '\''
                if typesDict[col_type] == 'char':
                    if col.length > -1:
                        col_data = '\', %s' % (str(col.length))
                elif typesDict[col_type] == 'decimal':
                    if col.precision > -1 and col.scale > -1:
                        col_data = '\', %s, %s' % (str(col.precision), str(col.scale))
                elif typesDict[col_type] == 'double':
                    if col.precision > -1 and col.length > -1:
                        col_data = '\', %s, %s' % (str(col.length), str(col.precision))
                elif typesDict[col_type] == 'enum':
                    col_data = '\', [%s]' % (col.datatypeExplicitParams[1:-1])
                elif typesDict[col_type] == 'string':
                    if col.length > -1:
                        col_data = '\', %s' % (str(col.length))

                if col.name == 'remember_token' and typesDict[col_type] == 'string' and str(col.length) == 100:
                    migrations[tbl.name].append('            $table->rememberToken();\n')
                elif(typesDict[col_type]) :
                    migrations[tbl.name].append('            $table->%s(\'%s%s)' % (typesDict[col_type], col.name, col_data))
                    if typesDict[col_type] == 'integer' and 'UNSIGNED' in col.flags:
                        migrations[tbl.name].append('->unsigned()')
                    if col.isNotNull != 1:
                        migrations[tbl.name].append('->nullable()')
                    if col.defaultValue != '' and col.defaultValueIsNull != 0:
                        migrations[tbl.name].append('->default(NULL)')
                    elif col.defaultValue != '':
                        migrations[tbl.name].append('->default(%s)' % (col.defaultValue))
                    if col.comment != '':
                        migrations[tbl.name].append('->comment(\'%s\')' % (col.comment))
                    migrations[tbl.name].append(";")
                    migrations[tbl.name].append('\n')

            if deleted_at is True:
                migrations[tbl.name].append('            $table->softDeletes();\n')
            if timestamps is True:
                migrations[tbl.name].append('            $table->timestamps();\n')
            elif timestamps_nullable is True:
                migrations[tbl.name].append('            $table->nullableTimestamps();\n')

            first_foreign_created = 0
            for fkey in tbl.foreignKeys:
                if fkey.name != '':
                    if fkey.referencedColumns[0].owner.name in migration_tables:
                        if first_foreign_created == 0:
                            migrations[tbl.name].append('\n')
                            first_foreign_created = 1
                        migrations[tbl.name].append('            $table->foreign(\'%s\')->references(\'%s\')->on(\'%s\')->onDelete(\'%s\')->onUpdate(\'%s\');' % (fkey.columns[0].name, fkey.referencedColumns[0].name, fkey.referencedColumns[0].owner.name, fkey.deleteRule.lower(), fkey.updateRule.lower()))
                        migrations[tbl.name].append('\n')
                    else:
                        if fkey.referencedColumns[0].owner.name not in foreign_keys:
                            foreign_keys[fkey.referencedColumns[0].owner.name] = []
                        foreign_keys[fkey.referencedColumns[0].owner.name].append({'table':fkey.columns[0].owner.name, 'name':fkey.columns[0].name, 'referenced_table':fkey.referencedColumns[0].owner.name, 'referenced_name':fkey.referencedColumns[0].name, 'update_rule':fkey.updateRule, 'delete_rule':fkey.deleteRule})
            migrations[tbl.name].append("        });\n")
            for fkey, fval in foreign_keys.iteritems():
                if fkey == tbl.name:
                    keyed_tables = []
                    schema_table = 0
                    for item in fval:
                        if item['table'] not in keyed_tables:
                            keyed_tables.append(item['table'])
                            if schema_table == 0:
                                migrations[tbl.name].append('\n')
                                migrations[tbl.name].append('        Schema::table(\'%s\', function (Blueprint $table) {\n' % (item['table']))
                                schema_table = 1
                            migrations[tbl.name].append('            $table->foreign(\'%s\')->references(\'%s\')->on(\'%s\')->onDelete(\'%s\')->onUpdate(\'%s\');\n' % (item['name'], item['referenced_name'], item['referenced_table'], item['delete_rule'].lower(), item['update_rule'].lower()))
                    if schema_table == 1:
                        migrations[tbl.name].append("        });\n")
                        migrations[tbl.name].append('\n')

            migrations[tbl.name].append('    }\n')
            migrations[tbl.name].append('\n')
            migrations[tbl.name].append('    /**\n')
            migrations[tbl.name].append('     * Reverse the migrations.\n')
            migrations[tbl.name].append('     *\n')
            migrations[tbl.name].append('     * @return void\n')
            migrations[tbl.name].append('     */\n')
            migrations[tbl.name].append('    public function down()\n')
            migrations[tbl.name].append('    {\n')

            first_foreign_created = 0
            for fkey in tbl.foreignKeys:
                if fkey.name != '':
                    if fkey.referencedColumns[0].owner.name in migration_tables:
                        if first_foreign_created == 0:
                            migrations[tbl.name].append('        Schema::table(\'%s\', function (Blueprint $table) {\n' % (tbl.name))
                            first_foreign_created = 1
                        migrations[tbl.name].append('            $table->dropForeign([\'%s\']);\n' % (fkey.columns[0].name))
            if first_foreign_created == 1:
                migrations[tbl.name].append("        });\n")
                migrations[tbl.name].append('\n')

            for fkey, fval in foreign_keys.iteritems():
                if fkey == tbl.name:
                    keyed_tables = []
                    schema_table = 0
                    for item in fval:
                        if item['table'] not in keyed_tables:
                            keyed_tables.append(item['table'])
                            if schema_table == 0:
                                migrations[tbl.name].append('        Schema::table(\'%s\', function (Blueprint $table) {\n' % (item['table']))
                                schema_table = 1
                            migrations[tbl.name].append('            $table->dropForeign([\'%s\']);\n' % (item['name']))
                    if schema_table == 1:
                        migrations[tbl.name].append("        });\n")
                        migrations[tbl.name].append('\n')

            migrations[tbl.name].append('        Schema::drop(\'%s\');\n' % (tbl.name))
            migrations[tbl.name].append('    }\n')
            migrations[tbl.name].append('}')

        return migrations

    out = cStringIO.StringIO()

    try:
        for schema in [(s, s.name == 'main') for s in cat.schemata]:
            migrations = export_schema(out, schema[0], schema[1])
    except GenerateLaravel5MigrationError as e:
        Workbench.confirm(e.typ, e.message)
        return 1

    for mkey in sorted(migrations):
        out.write(''.join(migrations[mkey]))
        out.write('\n\n\n')

    sql_text = out.getvalue()
    out.close()

    wizard = GenerateLaravel5MigrationWizard(sql_text)
    wizard.run()

    return 0

class GenerateLaravel5MigrationError(Exception):
    def __init__(self, typ, message):
        self.typ = typ
        self.message = message

    def __str__(self):
        return repr(self.typ) + ': ' + repr(self.message)

class GenerateLaravel5MigrationWizard_PreviewPage(WizardPage):
    def __init__(self, owner, sql_text):
        WizardPage.__init__(self, owner, 'Review Generated Migration(s)')

        self.save_button = mforms.newButton()
        self.save_button.enable_internal_padding(True)
        self.save_button.set_text('Save Migration(s) to Folder...')
        self.save_button.set_tooltip('Select the folder to save your migration(s) to.')
        self.save_button.add_clicked_callback(self.save_clicked)

        self.sql_text = mforms.newCodeEditor()
        self.sql_text.set_language(mforms.LanguageMySQL)
        self.sql_text.set_text(sql_text)

    def go_cancel(self):
        self.main.finish()

    def create_ui(self):
        button_box = mforms.newBox(True)
        button_box.set_padding(8)

        button_box.add(self.save_button, False, True)

        self.content.add_end(button_box, False, False)
        self.content.add_end(self.sql_text, True, True)

    def save_clicked(self):
        file_chooser = mforms.newFileChooser(self.main, mforms.OpenDirectory)
        if file_chooser.run_modal() == mforms.ResultOk:
            path = file_chooser.get_path()
            text = self.sql_text.get_text(False)

            i = 0
            now = datetime.datetime.now()
            for mkey in sorted(migrations):
                try:
                    with open(path + '/%s_%s_%s_%s_create_%s_table.php' % (now.strftime('%Y'), now.strftime('%m'), now.strftime('%d'), str(i).zfill(6), mkey), 'w+') as f:
                            f.write(''.join(migrations[mkey]))
                            i = i + 1
                except IOError as e:
                    mforms.Utilities.show_error(
                        'Save to File',
                        'Could not save to file "%s": %s' % (path, str(e)),
                        'OK')

class GenerateLaravel5MigrationWizard(WizardForm):
    def __init__(self, sql_text):
        WizardForm.__init__(self, None)

        self.set_name('generate_laravel_5_migration_wizard')
        self.set_title('Generate Laravel 5 Migration Wizard')

        self.preview_page = GenerateLaravel5MigrationWizard_PreviewPage(self, sql_text)
        self.add_page(self.preview_page)

migrations = {}
typesDict = {
    'BIGINCREMENTS':'bigIncrements', \
    'INCREMENTS':'increments', \
    'TINYINT':'tinyInteger', \
    'SMALLINT':'smallInteger', \
    'MEDIUMINT':'mediumInteger', \
    'INT':'integer', \
    'BIGINT':'bigInteger', \
    'FLOAT':'float', \
    'DOUBLE':'double', \
    'DECIMAL':'decimal', \
    'CHAR':'char', \
    'VARCHAR':'string', \
    'BINARY':'binary', \
    'VARBINARY':'', \
    'TINYTEXT':'text', \
    'TEXT':'text', \
    'MEDIUMTEXT':'mediumText', \
    'LONGTEXT':'longText', \
    'TINYBLOB':'binary', \
    'BLOB':'binary', \
    'MEDIUMBLOB':'binary', \
    'LONGBLOB':'binary', \
    'DATETIME':'dateTime', \
    'DATETIME_F':'dateTime', \
    'DATE':'date', \
    'DATE_F':'date', \
    'TIME':'time', \
    'TIME_F':'time', \
    'TIMESTAMP':'timestamp', \
    'TIMESTAMP_F':'timestamp', \
    'YEAR':'smallInteger', \
    'GEOMETRY':'', \
    'LINESTRING':'', \
    'POLYGON':'', \
    'MULTIPOINT':'', \
    'MULTILINESTRING':'', \
    'MULTIPOLYGON':'', \
    'GEOMETRYCOLLECTION':'', \
    'BIT':'', \
    'ENUM':'enum', \
    'SET':'', \
    'BOOLEAN':'boolean', \
    'BOOL':'boolean', \
    'FIXED':'', \
    'FLOAT4':'', \
    'FLOAT8':'', \
    'INT1':'tinyInteger', \
    'INT2':'smallInteger', \
    'INT3':'mediumInteger', \
    'INT4':'integer', \
    'INT8':'bigint', \
    'INTEGER':'integer', \
    'LONGVARBINARY':'', \
    'LONGVARCHAR':'', \
    'LONG':'', \
    'MIDDLEINT':'mediumInteger', \
    'NUMERIC':'decimal', \
    'DEC':'decimal', \
    'CHARACTER':'char'
}
