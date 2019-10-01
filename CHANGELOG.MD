#### Changelog

#####01 October 2019 - Fixed varchar mysql field as primary key

The issue:    
	
			Schema::create($this->tableName, function (Blueprint $table) {
				$table->engine = 'InnoDB';
				$table->increments('idvarchar_primary_key')->nullable();
			});
	

After adjusting the code the entry is generated properly:
	
			Schema::create($this->tableName, function (Blueprint $table) {
				$table->engine = 'InnoDB';
				$table->string('idvarchar_primary_key', 15)->primary();
			});
	

Testing:
	
			Schema::create($this->tableName, function (Blueprint $table) {
				$table->engine = 'InnoDB';
				$table->string('idvarchar_primary_key', 15)->primary();
				$table->string('another_varchar', 45);
			});
	


Hope it helps!    
A. Fulop