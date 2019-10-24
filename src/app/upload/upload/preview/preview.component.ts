import { Component, OnInit, TemplateRef } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick } from 'src/app/shared/models/brick';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { Router } from '@angular/router';

@Component({
  selector: 'app-preview',
  templateUrl: './preview.component.html',
  styleUrls: ['./preview.component.css']
})
export class PreviewComponent implements OnInit {

  modalRef: BsModalRef;

  constructor(
    private uploadService: UploadService,
    private modalService: BsModalService,
    private router: Router
  ) { }

  brick: Brick;

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    if (!this.brick || !this.brick.dataValues.length) {
      this.router.navigate(['/upload/type']);
    }
  }

  openModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(template);
  }

}
