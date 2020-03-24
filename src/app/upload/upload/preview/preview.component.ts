import { Component, OnInit, TemplateRef } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, TypedProperty, Term, ORef } from 'src/app/shared/models/brick';
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
	this.totalObjectsMapped = 0;
	if ((this.coreObjectRefs) && (this.coreObjectRefs.length > 0)) {
	   for (var x of this.coreObjectRefs) {
	      this.totalObjectsMapped += x.count;
	   }
	}
        this.brick.coreObjectRefsError = (this.totalObjectsMapped === 0);
      });
  }

  openModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(template);
  }

  getPropValueDisplay(prop: TypedProperty) {
    if (prop.scalarType === 'oterm_ref')
      return (prop.value as Term).text;
    else if (prop.scalarType === 'object_ref')
      return (prop.value as ORef).text;
      // return JSON.stringify(prop.value);
    else
      return prop.value;
  }

}
