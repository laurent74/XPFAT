# Xcode Project Files And Targets

List the files of an Xcode project and the targets they are included in.

## Usage Example

At minimum, pass in argument the full path of the .pbxproj to inspect.

Example:

	$ python3 ./work.py --pbxproj ./project.pbxproj

full options:

--supported-file-types: the file types to list (comma-separated). E.g.: m,swift,xib,storyboard. Leave empty to list them all
--ignore-test-files: if set, do not list the unit test files

Example:

	$ python3 ./work.py --pbxproj ./project.pbxproj --supported-file-types m,swift,xib,storyboard --ignore-test-files

## Help

Show the help for the script using:

	$ python3 ./work.py -h