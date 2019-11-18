import { Component, OnInit, ChangeDetectorRef, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { NgxSpinnerService } from 'ngx-spinner';
import 'datatables.net';
import 'datatables.net-bs4';
import * as $ from 'jquery';
@Component({
  selector: 'app-dimension-variable-preview',
  templateUrl: './dimension-variable-preview.component.html',
  styleUrls: ['./dimension-variable-preview.component.css']
})
export class DimensionVariablePreviewComponent implements OnInit, AfterViewInit {

  constructor(
  ) { }

  id: string;
  index: number;
  numberOfRows: number;
  data: any;
  dataResults: any[] = [];
  dataTable: any;

  @ViewChild('tableModal') el: ElementRef;

  ngOnInit() {
    this.dataResults = this.data.dim_vars;
    this.numberOfRows = this.data.size > this.data.max_row_count
      ? this.data.max_row_count
      : this.data.size;
  }

  ngAfterViewInit() {
    if (this.el) {
            const table: any = $(this.el.nativeElement);
            this.dataTable = table.DataTable();
          }
  }

}
