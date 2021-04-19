import { Component, OnInit } from '@angular/core';
import { UserService } from 'src/app/shared/services/user.service';
import { User } from 'src/app/shared/models/user';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { Response } from 'src/app/shared/models/response';

enum UploadMessageStream {
  SUCCESS = 'success',
  WARNING = 'warning',
  PROGRESS = 'progress',
  ERROR = 'error',
  COMPLETE = 'complete'
}
@Component({
  selector: 'app-core-type-upload-widget',
  templateUrl: './core-type-upload-widget.component.html',
  styleUrls: ['./core-type-upload-widget.component.css']
})
export class CoreTypeUploadWidgetComponent implements OnInit {

  constructor(
    private userService: UserService,
    private uploadService: UploadService,
    private router: Router
  ) { }

  file: File = null;
  fileSize: string;
  fileTypeError = false;
  uploadError = false; // 
  readyToUpload = false;
  selectedTypeError = false;
  validationError = false;
  validationErrorMessage: string;
  public loading = false;
  progressPercentage = 0;
  requiresProcessTSV = false;

  nSuccesses = 0;
  nWarnings = 0;
  nErrors = 0;
  
  user: User;
  public selectedType: string;
  allowedUploadTypes: string[];

  uploadProgressStream: Subscription;
  

  ngOnInit(): void {
    this.user = this.userService.getUser();
    if (this.user.allowed_upload_types === '*') {
      this.uploadService.getCoreTypeNames()
        .subscribe((data: any) => {
          this.allowedUploadTypes = data.results;
        })
    } else {
      this.allowedUploadTypes = this.user.allowed_upload_types as string[];
    }
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

  async upload() {
    if (this.file && !this.selectedType) {
      this.selectedTypeError = true;
      return;
    }

    try {
      await this.uploadService.validateCoreTypeTSV(this.selectedType, this.file)
      } catch(e) {
        this.validationError = true;
        this.validationErrorMessage = e.error;
        return;
      }

    this.loading = true;
    this.uploadProgressStream = this.uploadService.uploadCoreTypeTSV(this.selectedType, this.file)
      .subscribe((event: {data: string}) => {
        const [eventType, eventMessage] = event.data.split('--');
        switch (eventType) {
          case UploadMessageStream.PROGRESS:
            this.progressPercentage = +eventMessage * 100;
            break;
          case UploadMessageStream.SUCCESS:
            this.nSuccesses++;
            break;
          case UploadMessageStream.WARNING:
            this.nWarnings++;
            break;
          case UploadMessageStream.ERROR:
            this.nErrors++;
            break;
          case UploadMessageStream.COMPLETE:
            const batchId = eventMessage;
            this.uploadProgressStream.unsubscribe();
            this.router.navigate([`/core-type-result/${batchId}`])
            break;
          default:
            console.error(`Error: Unsupported message type "${eventType}"`);
        }
      });
  }

  clearFile() {
    this.file = null;
    this.readyToUpload = false;
    this.fileTypeError = false;
    this.uploadError = false;
    this.validationError = false;
    delete this.validationErrorMessage;
  }

  onTypeSelection() {
    this.selectedTypeError = false;
    this.uploadService.checkProvenanceOf(this.selectedType)
      .subscribe((data: any) => {
        this.requiresProcessTSV = data.results.requires_processes;
      })
  }

}
