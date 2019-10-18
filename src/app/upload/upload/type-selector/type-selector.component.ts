import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Select2OptionData } from 'ng2-select2';
import { Brick } from 'src/app/shared/models/brick';
import { environment } from 'src/environments/environment';
@Component({
  selector: 'app-type-selector',
  templateUrl: './type-selector.component.html',
  styleUrls: ['./type-selector.component.css']
})
export class TypeSelectorComponent implements OnInit {

  constructor(
    private uploadService: UploadService
  ) { }

  select2Options: Select2Options = {
    width: '100%',
    placeholder: 'Select a Data Type',
    containerCssClass: 'select2-custom-container'
  };

  select2Data: Array<Select2OptionData>;

  ajaxOptions: Select2AjaxOptions;
  private brick: Brick;
  dataTypes: any;
  selectedTemplate: string;

  ngOnInit() {
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

  setBrickType(event) {
    const template = event.data[0];
    this.uploadService.setSelectedTemplate(template);
    this.uploadService.testBrickBuilder();
  }

}
