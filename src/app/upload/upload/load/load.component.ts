import { Component, OnInit, OnDestroy } from '@angular/core';
import { UploadDragDropDirective } from 'src/app/shared/directives/upload-drag-drop.directive';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, TypedProperty, Term } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';
import { Subscription } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';


@Component({
  selector: 'app-load',
  templateUrl: './load.component.html',
  styleUrls: ['./load.component.css'],
  viewProviders: [UploadDragDropDirective]
})
export class LoadComponent implements OnInit, OnDestroy {

  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
    private validator: UploadValidationService
  ) { }

  file: File = null;
  fileSize: string;
  brick: Brick;
  successData: any;
  error = false;
  errorMessage: string;
  loading = false;
  validationError = false;
  validationErrorSub: Subscription

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.getUploadData();
    this.validationErrorSub = this.validator.getValidationErrors()
     .subscribe(error => this.validationError = error);
  }

  ngOnDestroy() {
    if (this.validationErrorSub) {
      this.validationErrorSub.unsubscribe();
    }
  }

  getUploadData() {
    const data = this.uploadService.uploadSuccessData;
    if (data) { this.successData = data; }

    const file: File = this.uploadService.uploadFile;
    if (file) {
      this.file = file;
      this.calculateFileSize();
    }
  }

  handleFileInput(files: FileList) {
    this.file = files.item(0);
    this.calculateFileSize();
    this.validationError = false;
   }

   handleFileInputFromBrowse(event) {
     if (event.target && event.target.files) {
       this.file = event.target.files.item(0);
       this.uploadService.setFile(this.file);
       // reset target value so that even can be triggered again
       event.target.value = null;
       this.calculateFileSize();
       this.validationError = false;
     }
   }

   calculateFileSize() {
    if (this.file.size > 1000000) {
      this.fileSize = `${this.file.size / 1000000} MB`;
    } else {
      this.fileSize = `${this.file.size / 1000} KB`;
    }
   }

   downloadTemplate() {
     this.uploadService.downloadBrickTemplate()
      .subscribe((data: Blob) => {
        const url = window.URL.createObjectURL(data);
        const a = document.createElement('a');
        document.body.appendChild(a);
        a.setAttribute('style', 'display: none');
        a.href = url;
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
      });
   }

   upload() {
    this.loading = true;
    this.spinner.show();
    this.uploadService.uploadBrick(this.file).then((res: any) => {
      this.loading = false;
      this.spinner.hide();
      this.successData = res.results;
      this.uploadService.setSuccessData(res.results);
    },
    err => {
      this.spinner.hide();
      this.error = true;
      this.errorMessage = err.error;
      this.loading = false;
    }
    );
    this.validationError = false;
   }

   removeFile() {
     this.file = null;
     this.error = false;
     delete this.errorMessage;
     delete this.successData;
     this.uploadService.setSuccessData(null);
     this.uploadService.setFile(null as File);
     this.validationError = false;
   }

}
