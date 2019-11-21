import { Component, OnInit } from '@angular/core';
import { Context } from 'src/app/shared/models/brick';
import { BsModalRef } from 'ngx-bootstrap/modal';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

@Component({
  selector: 'app-context-builder',
  templateUrl: './context-builder.component.html',
  styleUrls: ['./context-builder.component.css']
})
export class ContextBuilderComponent implements OnInit {

  public context: Context[];
  public title: string;
  error = false;
  errorMessages: string[] = [];

  constructor(
    public modalRef: BsModalRef,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
  }

  addContext() {
    this.context.push(new Context(false));
  }

  removeContext(index: number): void {
    this.context.splice(index, 1);
  }

  resetContext(event: Context, index: number) {
    this.context.splice(index, 1, event);
  }

  setValueError(event) {
    if (event) {
      this.error = true;
      this.errorMessages.push(event);
    } else {
      if (this.errorMessages.length === 1) {
        this.errorMessages = [];
        this.error = false;
      }
    }
  }

  onClose() {
    const errors = this.validator.validateContext(this.context);
    if (errors.length) {
      this.error = true;
      this.errorMessages = errors;
    } else {
      this.modalRef.hide();
    }
  }

}
