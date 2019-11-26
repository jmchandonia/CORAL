import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { BsModalRef } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-validation-error-item',
  templateUrl: './validation-error-item.component.html',
  styleUrls: ['./validation-error-item.component.css']
})
export class ValidationErrorItemComponent implements OnInit {

  index: number;
  dimVarIndex: number;
  errors = [];

  constructor(
    private uploadService: UploadService,
    private modalRef: BsModalRef
  ) { }

  ngOnInit() {
    if (!this.dimVarIndex) {
      // get errors for data variables
      this.uploadService.getDataVarValidationErrors(this.index)
        .subscribe((res: any) => {
          this.errors = res.results;
        });
    } else {
      // get errors for dimension variables
      this.uploadService.getDimVarValidationErrors(this.index, this.dimVarIndex)
        .subscribe((res: any) => {
          this.errors = res.results;
        });
    }
  }

  onClose() {
    this.modalRef.hide();
  }

}
