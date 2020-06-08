import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { BsModalRef } from 'ngx-bootstrap/modal';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';

@Component({
  selector: 'app-validation-error-item',
  templateUrl: './validation-error-item.component.html',
  styleUrls: ['./validation-error-item.component.css']
})
export class ValidationErrorItemComponent implements AfterViewInit {

  errors: any[];
  dataTable: any;
  @ViewChild('tableModal', { static: false }) el: ElementRef;

  constructor(
    private uploadService: UploadService,
    private modalRef: BsModalRef
  ) { }

  ngAfterViewInit() {
    if (this.el) {
      const table: any = $(this.el.nativeElement);
      this.dataTable = table.DataTable();
    }
  }

  onClose() {
    this.modalRef.hide();
  }

}
