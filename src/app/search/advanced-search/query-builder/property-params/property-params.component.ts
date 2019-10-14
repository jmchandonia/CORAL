import {
  Component,
  OnInit,
  Input,
  Output,
  EventEmitter,
  ViewChild,
  ElementRef
 } from '@angular/core';
import { Select2OptionData, Select2Component } from 'ng2-select2';
import { QueryParam } from '../../../../shared/models/QueryBuilder';
import { NetworkService } from '../../../../shared/services/network.service';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css'],
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  // @Output() added: EventEmitter<QueryParam> = new EventEmitter();
  @Input() queryParam: QueryParam;
  @Output() updated: EventEmitter<any> = new EventEmitter();
  @Input() isEmpty: boolean;
  @Input() set attributes(a: Array<any>) {
    if (a) {
      this.propertyTypesMetadata = a;
      this.propertyTypes = [this.propertyTypes[0], ...a.map((item, idx) => {
        return { id: idx.toString(), text: item.name };
      })];
    }
  }
  @Input() set operators(o: Array<string>) {
    if (o) {
      this.matchTypes = [this.matchTypes[0], ...o.map(item => {
        return { id: item, text: item };
      })];
    }
  }
  @Input() connection = '';
  @ViewChild(Select2Component) attribute: ElementRef;
  // @ViewChild(Select2Component) matchType: ElementRef;

  // queryParam: QueryParam;
  matchTypeBuilder = '';
  attributeBuilder = '';
  keywordBuilder = '';
  propertyTypesMetadata: any[];
  propertyTypes: Array<Select2OptionData> = this.select2Init();
  matchTypes: Array<Select2OptionData> = this.select2Init();
  selectedMatchType: string;
  selectedAttribute: string;

  select2Init() {
    // required to have placeholder be displayed
    return [{id: '', text: ''}];
  }

  // @Input() set data(param) {
  //   if (param.matchType) {
  //     this.selectedMatchType = param.matchType;
  //     this.matchTypes.push({id: '0', text: param.matchType});
  //     this.matchTypeBuilder = param.matchType;
  //   }
  //   if (param.attribute) {
  //     this.selectedAttribute = param.attribute;
  //     this.propertyTypes.push({id: '0', text: param.attribute});
  //     this.attributeBuilder = param.attribute;
  //   }
  //   this.keywordBuilder = param.keyword;
  //   this.queryParam = param;
  // }

  constructor(
    private network: NetworkService,
  ) { }

  ngOnInit() {
   }

  // addParam() {
  //   const scalar = this.propertyTypesMetadata.find(item => {
  //     return item.name === this.attributeBuilder;
  //   }).scalar_type;
  // }

  // TODO: add scalar type

  findDropdownValue(builder, dropDownType) {
    return this.propertyTypes.length > 1 ?
    this[dropDownType].find(item => item.text === builder).id
    : '';
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
