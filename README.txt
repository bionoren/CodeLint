Supported Languages:
Objective C
Any language that uses C-style bracket syntax

To ignore isseues, place "$ignore" as the very last text on a line
Example: else { //$ignore
WARNING: This will suppress ALL warnings associated with this line!
NOTE: For languages without a multiline comment syntax, you must close the comment on a new line
    Example: else { /* $ignore
             */

Known limitations:
Objective C lint assumes one interface per .h file and one implementation per .m file