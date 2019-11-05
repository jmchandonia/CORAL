import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
 } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryParam } from '../../../../shared/models/QueryBuilder';
import { QueryBuilderService } from '../../../../shared/services/query-builder.service';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css'],
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Input() queryParam: QueryParam;
  @Input() dataType: string;
  @Output() updated: EventEmitter<any> = new EventEmitter();

  propertyTypesMetadata: any[];
  propertyTypes: Array<Select2OptionData> = this.select2Init();
  matchTypes: Array<Select2OptionData> = this.select2Init();
  selectedMatchType: string;
  selectedAttribute: string;

  select2Init() {
    // required to have placeholder be displayed
    return [{id: '', text: ''}];
  }

  constructor(
    private queryBuilder: QueryBuilderService
  ) {
  }

  ngOnInit() {
    this.selectedMatchType = this.queryBuilder.getOperatorValue(this.queryParam.matchType);
    this.matchTypes = this.queryBuilder.getOperators();
    const attributes = this.queryBuilder.getAttributes(this.dataType);
    if (this.queryParam.attribute) {
      const s = attributes.find(item => {
        return item.name === this.queryParam.attribute;
      });
      this.selectedAttribute = attributes.indexOf(s).toString();
    }
    this.propertyTypesMetadata = attributes;
    this.propertyTypes = [{id: '', text: ''}, ...attributes.map((attr, idx) => {
      return {id: idx.toString(), text: attr.name};
    })];
   }

  updateParam(builder, event) {
    this.updated.emit({key: builder, value: event});
  }

  removeParam() {
    this.removed.emit();
  }

  setAttribute(event) {
    this.queryParam.attribute = event.data[0].text;
    this.setScalarType(parseInt(event.value, 10));
  }

  setScalarType(index) {
    this.queryParam.scalarType = this.propertyTypesMetadata[index].scalar_type;
  }

  setMatchType(event) {
    this.queryParam.matchType = event.data[0].text;
  }

}
