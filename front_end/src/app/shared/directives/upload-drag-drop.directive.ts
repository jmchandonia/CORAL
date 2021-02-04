import { Directive, Output, EventEmitter, HostBinding, HostListener } from '@angular/core';

@Directive({
  // tslint:disable-next-line:directive-selector
  selector: '[appUploadDragDrop]'
})
export class UploadDragDropDirective {

  constructor() { }

  @Output() fileDropped = new EventEmitter<any>();

  @HostBinding('style.background-color') background = '#eeeeff';

  @HostListener('dragenter', ['$event'])
  @HostListener('dragover', ['$event'])
  public onDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    this.background = '#ddddfc';
  }

  @HostListener('dragleave', ['$event']) public onDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    this.background = '#eeeeff';
  }

  @HostListener('drop', ['$event']) public onDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    const files = event.dataTransfer.files;
    if (files.length) {
      this.fileDropped.emit(files);
    }
    this.background = '#eeeeff';
  }

}
