import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-validation-error-item',
  templateUrl: './validation-error-item.component.html',
  styleUrls: ['./validation-error-item.component.css']
})
export class ValidationErrorItemComponent {

  errors: any[];
  dataTable: any;
  @ViewChild('tableModal') el: ElementRef;

  constructor(
    private modalRef: BsModalRef
  ) { }

  onClose() {
    this.modalRef.hide();
  }

}
