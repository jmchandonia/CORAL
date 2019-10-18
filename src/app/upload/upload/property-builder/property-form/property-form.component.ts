import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { TypedProperty } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
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

    if (!prop.editable) {
      this.typesSelect2 = [prop.type];
      this.unitsSelect2 = [prop.units];
    }

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
  // @Input() set propertyList(props: any[]) {
  //   this._propertyList = props;
  //   this.select2Data = props.map((prop, idx) => ({
  //     id: idx.toString(),
  //     text: this.format(prop.name)
  //   }));
  // }

  // get propertyList() {
  //   return this._propertyList;
  // }

  // private _propertyList: any[];
  private _property: TypedProperty;
  unitsSelect2: Array<Select2OptionData> = [];
  select2Options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container'
   };

   typesSelect2: Array<Select2OptionData> = [];

   propTypeItem: string;
   propValueItem: string;
   unitsItem: string;
   editable = true;

  constructor() { }

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
    const idx = parseInt(event.value, 10);
    this.property.type = event.data[0].text;
    this.property.units = this.propertyList[idx].scalar_type;
  }

  onDelete() {
    this.deleted.emit(this.property);
  }

}
