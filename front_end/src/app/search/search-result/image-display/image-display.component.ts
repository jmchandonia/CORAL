import { SafeUrl } from '@angular/platform-browser';
import { Component, OnInit, SecurityContext } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';
import { DomSanitizer } from '@angular/platform-browser';

@Component({
  selector: 'app-image-display',
  templateUrl: './image-display.component.html',
  styleUrls: ['./image-display.component.css']
})
export class ImageDisplayComponent implements OnInit {

  title: string;
  imgSrc: SafeUrl;

  constructor(
    private modalRef: BsModalRef,
    private sanitizer: DomSanitizer
  ) { }

  ngOnInit(): void {
  }

  closeModal() {
    this.modalRef.hide();
  }

  handleDownload() {
    const a = document.createElement('a');
    a.href = this.sanitizer.sanitize(SecurityContext.URL, this.imgSrc);
    a.download = this.title;
    a.click();
    a.remove();
  }

}
