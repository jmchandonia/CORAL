import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { BsModalRef } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-error',
  templateUrl: './error.component.html',
  styleUrls: ['./error.component.css']
})
export class ErrorComponent implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private modalRef: BsModalRef
  ) { }

  data: any;
  message: string;
  status: string;

  ngOnInit() {
  }

  onClose() {
    this.modalRef.hide();
  }

}
