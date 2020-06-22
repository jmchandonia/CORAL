import { Component, OnInit, OnDestroy, ViewEncapsulation } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick } from 'src/app/shared/models/brick';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-type-selector',
  templateUrl: './type-selector.component.html',
  styleUrls: ['./type-selector.component.css'],
  encapsulation: ViewEncapsulation.None

})
export class TypeSelectorComponent implements OnInit, OnDestroy {

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  templateData = [];
  errorSub: Subscription;
  brick: Brick;
  dataTypes: any;
  selectedTemplate: string;
  error = false;

  ngOnInit() {
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => {
        this.error = error;
      });
      
    this.selectedTemplate = this.uploadService.getSelectedTemplate();
    this.brick = this.uploadService.getBrickBuilder();
    const templates = this.uploadService.brickTypeTemplates;
    if (templates) {
      this.templateData = [...templates];
    } else {
      this.uploadService.getTemplateSub()
      .subscribe((data: any) => {
        this.templateData = [...data];
      });
    }
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  setBrickType(event) {
    this.uploadService.setSelectedTemplate(event);
    this.validate();
  }

  validate() {
    if (this.error) {
      this.validator.validateDataType();
    }
  }

}
