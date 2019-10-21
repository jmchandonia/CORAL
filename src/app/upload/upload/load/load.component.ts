import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-load',
  templateUrl: './load.component.html',
  styleUrls: ['./load.component.css']
})
export class LoadComponent implements OnInit {

  constructor() { }

  file: File = null;
  fileSize: string;

  ngOnInit() {
  }

  handleFileInput(files: FileList) {
    this.file = files.item(0);
    if (this.file.size > 1000000) {
      this.fileSize = `${this.file.size / 1000000} MB`;
    } else {
      this.fileSize = `${this.file.size / 1000} KB`;
    }
   }

}
