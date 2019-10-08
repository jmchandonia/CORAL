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

  @Output() deleted = new EventEmitter();
  @Input() property: TypedProperty;
  @Input() set propertyList(props: any[]) {
    this._propertyList = props;
    this.select2Data = props.map((prop, idx) => ({
      id: idx.toString(),
      text: this.format(prop.name)
    }));
  }

  get propertyList() {
    return this._propertyList;
  }

  private _propertyList: any[];
  select2Data: Array<Select2OptionData> = [];
  select2Options: Select2Options = { width: '100%' };

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
