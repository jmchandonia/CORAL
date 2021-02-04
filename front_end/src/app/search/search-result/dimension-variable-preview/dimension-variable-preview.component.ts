import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';
import { ColumnMode } from '@swimlane/ngx-datatable';
@Component({
  selector: 'app-dimension-variable-preview',
  templateUrl: './dimension-variable-preview.component.html',
  styleUrls: ['./dimension-variable-preview.component.css']
})
export class DimensionVariablePreviewComponent implements OnInit {

  constructor(
    public modalRef: BsModalRef
  ) { }

  id: string;
  index: number;
  title: string;
  numberOfRows: number;
  data: any;
  dataResults: any[] = [];
  dataTable: any;
  rows: any[];
  columnMode = ColumnMode

  @ViewChild('tableModal', { static: true }) el: ElementRef;

  ngOnInit() {
    this.dataResults = [...this.data.dim_vars];
    this.rows = this.dataResults[0].values.map((val, idx) => {
      const keys = {};
      this.dataResults.forEach(field => {
        keys[field.type_with_units] = field.values[idx]; 
      });
      return keys;
    });
    this.numberOfRows = this.data.size > this.data.max_row_count
      ? this.data.max_row_count
      : this.data.size;
  }

}
