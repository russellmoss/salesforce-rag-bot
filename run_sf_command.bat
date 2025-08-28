@echo off
powershell -ExecutionPolicy Bypass -File "C:\Users\russe\AppData\Roaming\npm\sf.ps1" data query --query "SELECT QualifiedApiName, Label, DataType, Description FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Contact' ORDER BY QualifiedApiName" --json --use-tooling-api -o NEWORG
