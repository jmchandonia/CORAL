import { Component, OnInit, OnDestroy, ViewEncapsulation } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Select2OptionData } from 'ng2-select2';
import { Brick } from 'src/app/shared/models/brick';
import { environment } from 'src/environments/environment';
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

  select2Options: Select2Options = {
    width: '100%',
    placeholder: 'Select a Data Type',
    containerCssClass: 'select2-custom-container'
  };

  select2Data: Array<Select2OptionData>;
  errorSub: Subscription;
  ajaxOptions: Select2AjaxOptions;
  brick: Brick;
  dataTypes: any;
  selectedTemplate: string;
  error = false;

  ngOnInit() {
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => {
        this.error = error;
      });

    this.selectedTemplate = this.uploadService.selectedTemplate;
    this.brick = this.uploadService.getBrickBuilder();
    const templates = this.uploadService.brickTypeTemplates;
    if (templates) {
      this.select2Data = templates;
    } else {
      this.uploadService.getTemplateSub()
      .subscribe((data: any) => {
        this.select2Data = data;
      });
    }
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  setBrickType(event) {
    const template = event.data[0];
    this.uploadService.setSelectedTemplate(template);
  }

}
