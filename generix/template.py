from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

def generate_brick_2d_template_draft(brick_skeleton,file_name):
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


def generate_brick_2d_template(brick_skeleton,file_name):

    TITLE_FONT = Font(name='Calibri', size=14) 
    INSTRUCTIONS_FONT = Font(name='Calibri', size=10, bold=True, italic=True)
    DIM1_FILL = PatternFill('solid', fgColor="FFFFDD")  
    DIM2_FILL = PatternFill('solid', fgColor="DDFFDD")
    DATA_FILL = PatternFill('solid', fgColor="FFDDDD") 
    COLUMN_WIDTH = 18
    dim1_row_counts = 10
    dim2_row_counts = 10

    FORMAT_NAME = 'F2D'


    book = Workbook()
    sheet = book.active

    data_vars = brick_skeleton['dataValues']
    brick_dims = brick_skeleton['dimensions']


    data_type = brick_skeleton['type']
    data_var = data_vars[0]['type']['text']

    dims = [brick_dims[0]['type']['text'], brick_dims[1]['type']['text']]
    dim1_vars = []
    for dim_var in brick_dims[0]['variables']:
        dim1_vars.append( '%s:%s' % (dims[0], dim_var['type']['text'])  )

    dim2_vars = []
    for dim_var in brick_dims[1]['variables']:
        dim2_vars.append('%s:%s' % (dims[1], dim_var['type']['text']) )

    rows = [
        ['Automatically generated template '],
        ['Type', data_type],    
        ['Dimension 1', dims[0]],
        ['Dimension 2', dims[1]],
        ['Data values', data_var],
        [],
        ['Instructions: fill in all colored parts of the spreadheet bellow with your data and metadata'],
        ['@Format:%s' % FORMAT_NAME]
    ]


    for j in range(len(dim2_vars) -1 ):
        row = []
        for i in range(len(dim1_vars)):
            row.append('')
        row.append(dim2_vars[j])
        rows.append(row)
        
    row = []
    for dim1_var in dim1_vars:
        row.append(dim1_var)
    row.append(dim2_vars[-1])
    rows.append(row)
        

    for row in rows:
        sheet.append(row)
        
    sheet['A1'].font = TITLE_FONT

    sheet['A3'].fill = DIM1_FILL
    sheet['B3'].fill = DIM1_FILL

    sheet['A4'].fill = DIM2_FILL 
    sheet['B4'].fill = DIM2_FILL 

    sheet['A5'].fill = DATA_FILL
    sheet['B5'].fill = DATA_FILL

    sheet['A7'].font = INSTRUCTIONS_FONT
    sheet['A8'].font = INSTRUCTIONS_FONT

    # Color Dim 1
    start_row = len(rows) + 1        
    start_column = 1
    for ri in range(start_row,start_row + dim1_row_counts):
        for ci,_ in enumerate(dim1_vars):
            sheet.cell(row=ri, column=ci+start_column).fill = DIM1_FILL 

    # Color Dim 2        
    start_row = len(rows) - len(dim2_vars) + 1       
    start_column = len(dim1_vars) + 2
    for ri,_ in enumerate(dim2_vars):
        for ci in range(start_column,start_column + dim2_row_counts):
            sheet.cell(row=ri+ start_row, column=ci ).fill = DIM2_FILL 
        
    # Color Data    
    start_row = len(rows) + 1       
    start_column = len(dim1_vars) + 2    
    for ri in range(start_row,start_row + dim1_row_counts):
        for ci in range(start_column,start_column + dim2_row_counts):
            sheet.cell(row=ri, column=ci ).fill = DATA_FILL 
        
        
    for i in range(1, len(dim1_vars) + 2 ):
        c = get_column_letter(i)
        sheet.column_dimensions[c].width = COLUMN_WIDTH   

    book.save(file_name)    
