import { Component, OnInit } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-warning',
  templateUrl: './warning.component.html',
  styleUrls: ['./warning.component.css']
})
export class WarningComponent implements OnInit {

  constructor(
    private modalRef: BsModalRef
  ) { }

  data: any;
  message: string;
  title: string;

  ngOnInit(): void {
  }

  onClose() {
    this.modalRef.hide();
  }

}
