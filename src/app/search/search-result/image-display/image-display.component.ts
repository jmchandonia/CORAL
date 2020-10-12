import { SafeUrl } from '@angular/platform-browser';
import { Component, OnInit } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-image-display',
  templateUrl: './image-display.component.html',
  styleUrls: ['./image-display.component.css']
})
export class ImageDisplayComponent implements OnInit {

  title: string;
  imgSrc: SafeUrl;

  constructor(private modalRef: BsModalRef) { }

  ngOnInit(): void {
  }

  closeModal() {
    this.modalRef.hide();
  }

}
