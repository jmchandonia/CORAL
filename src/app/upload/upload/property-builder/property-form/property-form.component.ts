import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { TypedProperty, Term } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
// tslint:disable:variable-name

@Component({
  selector: 'app-property-form',
  templateUrl: './property-form.component.html',
  styleUrls: ['./property-form.component.css']
})
export class PropertyFormComponent implements OnInit {
  selectedValue: any;
  @Output() deleted = new EventEmitter();
  @Input() set property(prop: TypedProperty) {

    this.typesSelect2 = prop.type ? [prop.type] : [];
    this.unitsSelect2 = prop.units ? [prop.units] : [];

    this._property = prop;

    if (prop.type) {
      this.propTypeItem = prop.type.id;
    }
    if (prop.units) {
      this.unitsItem = prop.units.id;
    }
    if (prop.value) {
      this.propValueItem = prop.value.text;
    }
  }

  get property() {
    return  this._property;
  }

  get valueItem() {
    return this.property.value ?
      this.property.value.text : '';
  }

  private _property: TypedProperty;
  unitsSelect2: Array<Select2OptionData> = [];
  propertiesOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntTerms(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

  unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchOntUnits(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };


   typesSelect2: Array<Select2OptionData> = [];

   propTypeItem: string;
   propValueItem: string;
   unitsItem: string;
   editable = true;

  constructor(private uploadService: UploadService) { }

  ngOnInit() {
  }

  delete() {
    this.deleted.emit();
  }

  format(propName) {
    return propName
      .replace('n_', 'number of ')
      .replace(/_/gi, ' ');
  }

  setPropertyType(event) {
    const item = event.data[0];
    this.property.type = new Term(item.id, item.text);
  }

  setUnits(event) {
    const item = event.data[0];
    this.property.units = new Term(item.id, item.text);
  }

  onDelete() {
    this.deleted.emit(this.property);
  }

}
