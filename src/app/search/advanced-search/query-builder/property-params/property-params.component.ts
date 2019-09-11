import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ElementRef } from '@angular/core';
import { Select2OptionData, Select2Component } from 'ng2-select2';
import { QueryParam } from '../../../../shared/models/QueryBuilder';
import { NetworkService } from '../../../../shared/services/network.service';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css']
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Output() added: EventEmitter<QueryParam> = new EventEmitter();
  @Output() updated: EventEmitter<any> = new EventEmitter();
  @Input() isEmpty: boolean;
  @Input() set attributes(a: Array<any>) {
    if (a) {
      this.propertyTypesMetadata = a;
      this.propertyTypes = [this.propertyTypes[0], ...a.map(item => {
      return { id: item.name, text: item.name };
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

  private queryParam: QueryParam;
  private matchTypeBuilder = '';
  private attributeBuilder = '';
  private keywordBuilder = '';
  private propertyTypesMetadata: any[];
  private propertyTypes: Array<Select2OptionData> = this.select2Init();
  private matchTypes: Array<Select2OptionData> = this.select2Init();

  select2Init() {
    // required to have placeholder be displayed
    return [{id: '', text: ''}];
  }

  @Input() set data(param) {
    this.matchTypeBuilder = param.matchType;
    this.attributeBuilder = param.attribute;
    this.keywordBuilder = param.keyword;
    // TODO: figure out a way to bind builder values with select2 dropdown items
  }

  constructor(
    private network: NetworkService,
  ) { }

  ngOnInit() {
    // if (!this.isEmpty) {
    //   let newData = this.network.getPropertyValuesDirect(this.connection);
    //   newData = newData.map(item => {
    //     return { id: item.id.toString(), text: item.title };
    //   });
    //   this.propertyTypes = [this.propertyTypes[0], ...newData];
    // } else {
    //   this.network.getPropertyValues()
    //   .subscribe(data => {
    //     if (
    //         data.connection === this.connection 
    //         || (!this.connection && data.connection === 'queryMatch')
    //       ) {
    //      const newData = data.results.map(item => {
    //        return { id: item.id.toString(), text: item.title }
    //      });
    //      this.propertyTypes = [this.propertyTypes[0], ...newData];
    //     }
    //   });
    // }
  }

  addParam() {

    const scalar = this.propertyTypesMetadata.find(item => {
      return item.name === this.attributeBuilder;
    }).scalar_type;

    this.added.emit(new QueryParam(
      this.attributeBuilder,
      this.matchTypeBuilder,
      this.keywordBuilder,
      scalar
    ));
    this.attributeBuilder = '';
    this.matchTypeBuilder = '';
    this.keywordBuilder = '';
  }

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
    // you need to clear the builders here
  }

}
