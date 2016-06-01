# -*- coding: utf-8 -*-
# MySQL Workbench module
# A MySQL Workbench plugin which exports a Model to Laravel 5 Migrations
# Written in MySQL Workbench 6.3.6

import re
import StringIO

import grt
import mforms

from grt.modules import Workbench
from wb import DefineModule, wbinputs
from workbench.ui import WizardForm, WizardPage
from mforms import newButton, newCodeEditor, FileChooser

ModuleInfo = DefineModule(name='GenerateLaravel5Migration',
                          author='Brandon Eckenrode',
                          version='0.1.0')

@ModuleInfo.plugin('wb.util.generateLaravel5Migration',
                   caption='Export Laravel 5 Migration',
                   input=[wbinputs.currentCatalog()],
                   groups=['Catalog/Utilities', 'Menu/Catalog'])
@ModuleInfo.export(grt.INT, grt.classes.db_Catalog)

def generateLaravel5Migration(cat):
    def export_schema(out, schema, is_main_schema):
        if len(schema.tables) == 0:
            return

        for tbl in schema.tables:
            out.write('<?php\n')
            out.write('\n')
            out.write('use Illuminate\Database\Schema\Blueprint;\n')
            out.write('use Illuminate\Database\Migrations\Migration;\n')
            out.write('\n')
            out.write('class Create')
            components = tbl.name.split('_')
            out.write("".join(x.title() for x in components[0:]))
            out.write('Table extends Migration\n')
            out.write('{\n')
            out.write('    /**\n')
            out.write('     * Run the migrations.\n')
            out.write('     *\n')
            out.write('     * @return void\n')
            out.write('     */\n')
            out.write('    public function up()\n')
            out.write('    {\n')
            out.write("        Schema::create('" + tbl.name + "', function (Blueprint $table) {\n")

            for col in tbl.columns:
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

                col_data = "'"
                if format_type(col_type) == 'char':
                    if col.length > -1:
                        col_data = "', " + str(col.length)
                elif format_type(col_type) == 'decimal':
                    if col.precision > -1 and col.scale > -1:
                        col_data = "', " + str(col.precision) + ", " + str(col.scale)
                elif format_type(col_type) == 'double':
                    if col.precision > -1 and col.length > -1:
                        col_data = "', " + str(col.length) + ", " + str(col.precision)
                elif format_type(col_type) == 'enum':
                    col_data = "', [" + col.datatypeExplicitParams[1:-1] + "]"
                elif format_type(col_type) == 'string':
                    if col.length > -1:
                        col_data = "', " + str(col.length)

                if(format_type(col_type)) :
                    out.write("            $table->" + format_type(col_type) + "('" + col.name + col_data + ")")
                    if format_type(col_type) == 'integer' and 'UNSIGNED' in col.flags:
                        out.write("->unsigned()")
                    if col.isNotNull != 1:
                        out.write("->nullable()")
                    if col.defaultValue != '' and col.defaultValueIsNull != 0:
                        out.write("->default(NULL)")
                    elif col.defaultValue != '':
                        out.write("->default(" + col.defaultValue + ")")
                    if col.comment != '':
                        out.write("->comment('" + col.comment + "')")
                    out.write(";")
                    out.write('\n')

            out.write("        });\n")
            out.write('    }\n')
            out.write('\n')
            out.write('    /**\n')
            out.write('     * Reverse the migrations.\n')
            out.write('     *\n')
            out.write('     * @return void\n')
            out.write('     */\n')
            out.write('    public function down()\n')
            out.write('    {\n')
            out.write("        Schema::drop('" + tbl.name + "');\n")
            out.write('    }\n')
            out.write('}\n\n\n')

    def format_type(col_type):
        typesDict = {}
        typesDict["BIGINCREMENTS"] = "bigIncrements"
        typesDict["INCREMENTS"] = "increments"
        typesDict["TINYINT"] = "tinyInteger"
        typesDict["SMALLINT"] = "smallInteger"
        typesDict["MEDIUMINT"] = "mediumInteger"
        typesDict["INT"] = "integer"
        typesDict["BIGINT"] = "bigInteger"
        typesDict["FLOAT"] = "float"
        typesDict["DOUBLE"] = "double"
        typesDict["DECIMAL"] = "decimal"
        typesDict["CHAR"] = "char"
        typesDict["VARCHAR"] = "string"
        typesDict["BINARY"] = "binary"
        typesDict["VARBINARY"] = ""
        typesDict["TINYTEXT"] = ""
        typesDict["TEXT"] = "text"
        typesDict["MEDIUMTEXT"] = "mediumText"
        typesDict["LONGTEXT"] = "longText"
        typesDict["TINYBLOB"] = ""
        typesDict["BLOB"] = "binary"
        typesDict["MEDIUMBLOB"] = ""
        typesDict["LONGBLOB"] = ""
        typesDict["DATETIME"] = "dateTime"
        typesDict["DATETIME_F"] = "dateTime"
        typesDict["DATE"] = "date"
        typesDict["DATE_F"] = "date"
        typesDict["TIME"] = "time"
        typesDict["TIME_F"] = "time"
        typesDict["TIMESTAMP"] = "timestamp"
        typesDict["TIMESTAMP_F"] = "timestamp"
        typesDict["YEAR"] = "smallInteger"
        typesDict["GEOMETRY"] = ""
        typesDict["LINESTRING"] = ""
        typesDict["POLYGON"] = ""
        typesDict["MULTIPOINT"] = ""
        typesDict["MULTILINESTRING"] = ""
        typesDict["MULTIPOLYGON"] = ""
        typesDict["GEOMETRYCOLLECTION"] = ""
        typesDict["BIT"] = ""
        typesDict["ENUM"] = "enum"
        typesDict["SET"] = ""
        typesDict["BOOLEAN"] = "boolean"
        typesDict["BOOL"] = "boolean"
        typesDict["FIXED"] = ""
        typesDict["FLOAT4"] = ""
        typesDict["FLOAT8"] = ""
        typesDict["INT1"] = "tinyInteger"
        typesDict["INT2"] = "smallInteger"
        typesDict["INT3"] = "mediumInteger"
        typesDict["INT4"] = "integer"
        typesDict["INT8"] = "bigint"
        typesDict["INTEGER"] = "integer"
        typesDict["LONGVARBINARY"] = ""
        typesDict["LONGVARCHAR"] = ""
        typesDict["LONG"] = ""
        typesDict["MIDDLEINT"] = "mediumInteger"
        typesDict["NUMERIC"] = "decimal"
        typesDict["DEC"] = "decimal"
        typesDict["CHARACTER"] = "char"

        if(col_type in typesDict):
            return typesDict[col_type]
        else:
            return false

    out = StringIO.StringIO()

    try:
        for schema in [(s, s.name == 'main') for s in cat.schemata]:
            export_schema(out, schema[0], schema[1])
    except GenerateLaravel5MigrationError as e:
        Workbench.confirm(e.typ, e.message)
        return 1

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
        WizardPage.__init__(self, owner, 'Review Generated Script')

        self.save_button = mforms.newButton()
        self.save_button.enable_internal_padding(True)
        self.save_button.set_text('Save to File...')
        self.save_button.set_tooltip('Save the text to a new file.')
        self.save_button.add_clicked_callback(self.save_clicked)

        self.copy_button = mforms.newButton()
        self.copy_button.enable_internal_padding(True)
        self.copy_button.set_text('Copy to Clipboard')
        self.copy_button.set_tooltip('Copy the text to the clipboard.')
        self.copy_button.add_clicked_callback(self.copy_clicked)

        self.sql_text = mforms.newCodeEditor()
        self.sql_text.set_language(mforms.LanguageMySQL)
        self.sql_text.set_text(sql_text)

    def go_cancel(self):
        self.main.finish()

    def create_ui(self):
        button_box = mforms.newBox(True)
        button_box.set_padding(8)

        button_box.add(self.save_button, False, True)
        button_box.add(self.copy_button, False, True)

        self.content.add_end(button_box, False, False)
        self.content.add_end(self.sql_text, True, True)

    def save_clicked(self):
        file_chooser = mforms.newFileChooser(self.main, mforms.SaveFile)
        file_chooser.set_extensions('SQL Files (*.sql)|*.sql', 'sql')
        if file_chooser.run_modal() == mforms.ResultOk:
            path = file_chooser.get_path()
            text = self.sql_text.get_text(False)
            try:
                with open(path, 'w+') as f:
                    f.write(text)
            except IOError as e:
                mforms.Utilities.show_error(
                    'Save to File',
                    'Could not save to file "%s": %s' % (path, str(e)),
                    'OK')

    def copy_clicked(self):
        mforms.Utilities.set_clipboard_text(self.sql_text.get_text(False))

class GenerateLaravel5MigrationWizard(WizardForm):
    def __init__(self, sql_text):
        WizardForm.__init__(self, None)

        self.set_name('generate_laravel_5_migration_wizard')
        self.set_title('Generate Laravel 5 Migration Wizard')

        self.preview_page = GenerateLaravel5MigrationWizard_PreviewPage(self, sql_text)
        self.add_page(self.preview_page)
