import { Component, OnInit } from '@angular/core';
import { UserService } from 'src/app/shared/services/user.service';
import { User } from 'src/app/shared/models/user';
import { UploadService } from 'src/app/shared/services/upload.service';
import { HttpEvent, HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-core-type-upload-widget',
  templateUrl: './core-type-upload-widget.component.html',
  styleUrls: ['./core-type-upload-widget.component.css']
})
export class CoreTypeUploadWidgetComponent implements OnInit {

  constructor(
    private userService: UserService,
    private uploadService: UploadService
  ) { }

  file: File = null;
  fileSize: string;
  fileTypeError = false;
  uploadError = false; // 
  readyToUpload = false;
  selectedTypeError = false;
  public loading = false;
  progressPercentage = 0;

  nSuccesses = 0;
  nWarnings = 0;
  nErrors = 0;
  
  user: User;
  public selectedType: string;

  ngOnInit(): void {
    this.user = this.userService.getUser();
  }

  handleFileInput(files: FileList) {
    this.fileTypeError = false;
    this.uploadError = false;

    this.file = files.item(0);
    if (this.file?.type !== 'text/tab-separated-values') {
      this.fileTypeError = true;
    } else {
      this.calculateFileSize();
      this.readyToUpload = true;
    }
  }

  handleFileInputFromBrowse(event) {
    this.fileTypeError = false;
    this.uploadError = false;

    this.file = event.target?.files?.item(0);
    if (this.file?.type !== 'text/tab-separated-values') {
      this.fileTypeError = true;
    } else {
      this.calculateFileSize();
      this.readyToUpload = true;
    }
  }

  calculateFileSize() {
    if (this.file.size > 1000000) {
      this.fileSize = `${this.file.size / 1000000} MB`;
    } else {
      this.fileSize = `${this.file.size / 1000} KB`;
    }
  }

  upload() {
    if (this.file && !this.selectedType) {
      this.selectedTypeError = true;
      return;
    }
    this.loading = true;
    this.uploadService.uploadCoreTypeTSV(this.selectedType, this.file)
      .subscribe((event: any) => {
        if (event.data.includes('progress-')) {
          this.progressPercentage = +event.data.split('progress-')[1] * 100
        } else if (event.data.includes('success-')) {
          this.nSuccesses++;
        } else if (event.data.includes('warning-')) {
          this.nWarnings++;
        } else if (event.data.includes('error-')) {
          this.nErrors++;
        }
      });
  }

  clearFile() {
    this.file = null;
    this.readyToUpload = false;
    this.fileTypeError = false;
    this.uploadError = false;
  }

  clearSelectionError() {
    this.selectedTypeError = false;
  }

}
