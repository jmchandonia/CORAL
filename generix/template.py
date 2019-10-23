from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

def generate_brick_2d_template(brick_template,file_name):
    book = Workbook()
    sheet = book.active

    dims = ['Gene', 'Condition']

    dim1_vars = ['Gene:orgId', 'Gene:locusId']
    dim1_row_counts = 10

    dim2_vars = ['Condition:name', 'Condition:time']
    dim2_row_counts = 10

    data_type ='TNSeq<Gene, Condition>'

    rows = [
        ['Automatically generated template '],
        ['Data type', 'TNSeq<Gene, Condition>'],
        [],
        ['Instructions: fill in all colored parts of the spreadheet with your data and metadata'],
        ['Gene metadata'],
        ['Condition metadata'],
        ['Data'],    
        [],
        [],
        ['Format: F2D', '', 'Condition:name'],
        ['Gene:orgId', 'Gene:locusId', 'Condition:time']
    ]

    for row in rows:
        sheet.append(row)

    dim1_fill = PatternFill('solid', fgColor="FFFFDD")  
    dim2_fill = PatternFill('solid', fgColor="DDFFDD")
    data_fill = PatternFill('solid', fgColor="FFDDDD")  
        
    sheet['A1'].font = Font(name='Calibri', size=14)
    sheet['A4'].font = Font(name='Calibri', size=12, bold=True, italic=True)
    sheet['A5'].fill = dim1_fill
    sheet['A6'].fill = dim2_fill 
    sheet['A7'].fill = data_fill
    sheet['A10'].font = Font(name='Calibri', size=12, bold=True)

    start_row = 12        
    start_column = 1
    for ri in range(start_row,start_row + dim1_row_counts):
        for ci,_ in enumerate(dim1_vars):
            sheet.cell(row=ri, column=ci+start_column).fill = dim1_fill 

    start_row = 10        
    start_column = len(dim2_vars) + 2
    for ri,_ in enumerate(dim2_vars):
        for ci in range(start_column,start_column + dim2_row_counts):
            sheet.cell(row=ri+ start_row, column=ci ).fill = dim2_fill 
        
    start_row = 12      
    start_column = len(dim2_vars) + 2    
    for ri in range(start_row,start_row + dim1_row_counts):
        for ci in range(start_column,start_column + dim2_row_counts):
            sheet.cell(row=ri, column=ci ).fill = data_fill 
        
        
    for i in range(1, len(dim2_vars) + 2 ):
        c = get_column_letter(i)
        sheet.column_dimensions[c].width = 18    

    book.save(file_name)    
