import { Component, OnInit, TemplateRef } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, TypedProperty, Term } from 'src/app/shared/models/brick';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { Router } from '@angular/router';

@Component({
  selector: 'app-preview',
  templateUrl: './preview.component.html',
  styleUrls: ['./preview.component.css']
})
export class PreviewComponent implements OnInit {

  modalRef: BsModalRef;
  coreObjectRefs: any[] = [];
  totalObjectsMapped = 0;
  // coreObjectError = false;

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
    this.uploadService.getRefsToCoreObjects()
      .subscribe((res: any) => {
        this.coreObjectRefs = res.results;
        this.totalObjectsMapped = this.coreObjectRefs.length
          ? this.coreObjectRefs.reduce((a, c) => a.count + c.count) : 0;
        this.brick.coreObjectRefsError = this.totalObjectsMapped === 0;
      });
  }

  openModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(template);
  }

  getPropValueDisplay(prop: TypedProperty) {
    return prop.scalarType === 'oterm_ref'
      ? (prop.value as Term).text
      : prop.value;
  }

}
