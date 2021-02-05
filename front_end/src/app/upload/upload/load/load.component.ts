import { Component, OnInit, OnDestroy } from '@angular/core';
import { UploadDragDropDirective } from 'src/app/shared/directives/upload-drag-drop.directive';
import { UploadService } from 'src/app/shared/services/upload.service';
import { NgxSpinnerService } from 'ngx-spinner';
import { Subscription } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Brick } from 'src/app/shared/models/brick';


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
  successData: any;
  error = false;
  errorMessage: string;
  loading = false;
  validationError = false;
  validationErrorSub: Subscription;
  public brick: Brick;
  templateTypeError = false;

  templateTypeOptions: {type: string, text: string}[] = [
    {type: 'interlace', text: 'Interlace all data on same page'},
  ];

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.setTemplateTypeOptions();
    this.getUploadData();
    this.validationErrorSub = this.validator.getValidationErrors()
     .subscribe(error => this.validationError = error);
  }

  ngOnDestroy() {
    if (this.validationErrorSub) {
      this.validationErrorSub.unsubscribe();
    }
  }

  setTemplateTypeOptions() {
    if (this.brick.dimensions.length < 2) return;
    if (this.brick.dataValues.length > 1) {
      this.templateTypeOptions.push({
        type: 'tab_data',
        text: 'Spread individual data vars across tabs'
      });
    }
    if (this.brick.dimensions.length > 2) {
      this.templateTypeOptions.push({
        type: 'tab_dims',
        text: `Spread out ${this.brick.dimensions[this.brick.dimensions.length - 1].type.text} across tabs`
      });
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
    this.successData = null;
    this.error = false;
    this.file = files.item(0);
    this.uploadService.setFile(this.file);
    this.calculateFileSize();
    this.validationError = false;
   }

   handleFileInputFromBrowse(event) {
     this.successData = null;
     this.error = false;
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
     if (this.templateTypeOptions.length > 1 && !this.brick.sheet_template_type) {
       this.templateTypeError = true;
       return;
     }
     this.templateTypeError = false;
     this.uploadService.downloadBrickTemplate()
      .then((data: Blob) => {
        this.addUrlToPageAndClick(data);
      });
   }

   addUrlToPageAndClick(data: Blob) {
    const url = window.URL.createObjectURL(data);
    const a = document.createElement('a');
    document.body.appendChild(a);
    a.setAttribute('style', 'display: none');
    a.href = url;
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
   }

   upload() {
    this.loading = true;
    this.spinner.show();
    this.successData = null;
    this.uploadService.uploadBrick(this.file).then((res: any) => {
      this.loading = false;
      this.spinner.hide();
      this.error = false;
      delete this.errorMessage;
      this.successData = res.results;
      this.uploadService.setSuccessData(res.results);
    },
    err => {
      this.spinner.hide();
      this.error = true;
      this.errorMessage = err;
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
