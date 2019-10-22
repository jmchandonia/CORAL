import { Component, OnInit } from '@angular/core';
import { UploadDragDropDirective } from 'src/app/shared/directives/upload-drag-drop.directive';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, TypedProperty, Term } from 'src/app/shared/models/brick';


@Component({
  selector: 'app-load',
  templateUrl: './load.component.html',
  styleUrls: ['./load.component.css'],
  viewProviders: [UploadDragDropDirective]
})
export class LoadComponent implements OnInit {

  constructor(private uploadService: UploadService) { }

  file: File = null;
  fileSize: string;
  brick: Brick;

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

   upload() {
    this.uploadService.uploadBrick(this.file);
   }

   removeFile() {
     this.file = null;
   }

}
