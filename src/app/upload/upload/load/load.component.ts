import { Component, OnInit } from '@angular/core';
import { UploadDragDropDirective } from 'src/app/shared/directives/upload-drag-drop.directive';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, TypedProperty, Term } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';


@Component({
  selector: 'app-load',
  templateUrl: './load.component.html',
  styleUrls: ['./load.component.css'],
  viewProviders: [UploadDragDropDirective]
})
export class LoadComponent implements OnInit {

  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
  ) { }

  file: File = null;
  fileSize: string;
  brick: Brick;
  successData: any;
  error = false;
  loading = false;

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
  }

  handleFileInput(files: FileList) {
    this.file = files.item(0);
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
    },
    err => {
      this.spinner.hide();
      this.error = true;
    }
    );
   }

   removeFile() {
     this.file = null;
   }

}
