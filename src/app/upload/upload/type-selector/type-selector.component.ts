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
    placeholder: 'Select a Data Type'
  };

  select2Data: Array<Select2OptionData>;

  ajaxOptions: Select2AjaxOptions;
  private brick: Brick;
  dataTypes: any;

  ngOnInit() {

    this.brick = this.uploadService.getBrickBuilder();

    this.ajaxOptions = {
      url: `${environment.baseURL}/data_types`,
      dataType: 'json',
      processResults: (data: any) => {
        this.dataTypes = data.results.filter(item => item.dataModel === 'Brick');
        return {
          results: $.map(this.dataTypes, (obj, idx) => {
          return {id: idx.toString(), text: obj.dataType};
        })
      };
      }
    };
    this.select2Options.ajax = this.ajaxOptions;
  }

  setBrickType(event) {
    this.brick.type = event.data[0].text;
    this.uploadService.testBrickBuilder();
  }

}
