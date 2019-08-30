import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ElementRef } from '@angular/core';
import { Select2OptionData, Select2Component } from 'ng2-select2';
import { QueryParam } from '../../../../shared/models/QueryBuilder';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css']
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Output() added: EventEmitter<QueryParam> = new EventEmitter();
  @Output() updated: EventEmitter<any> = new EventEmitter();
  @Input() isEmpty = false;
  @ViewChild(Select2Component) attribute: ElementRef;

  private queryParam: QueryParam;
  private matchTypeBuilder = '';
  private attributeBuilder = '';
  private keywordBuilder = '';

  private propertyTypes: Array<Select2OptionData> = [
    {
      id: '',
      text: ''
    },
    {
      id: '0',
      text: 'name'
    },
    {
      id: '1',
      text: 'campaign name'
    },
    {
      id: '2',
      text: 'created by'
    },

  ]

  private matchTypes: Array<Select2OptionData> = [
    {
      id: '0',
      text: 'Match'
    },
    {
      id: '1',
      text: 'Contains'
    }
  ]

  @Input() set data(param) {
    this.matchTypeBuilder = param.matchType;
    this.attributeBuilder = param.attribute;
    this.keywordBuilder = param.keyword;
    // TODO: figure out a way to bind builder values with select2 dropdown items
  }

  constructor() { }

  ngOnInit() {
  }

  addParam() {
    this.added.emit(new QueryParam(
      this.attributeBuilder,
      this.matchTypeBuilder,
      this.keywordBuilder
    ));
    this.attributeBuilder = '';
    this.matchTypeBuilder = '';
    this.keywordBuilder = '';
  }

  findDropdownValue(builder) {
    return this.propertyTypes.find(item => item.text === builder).id
  }

  updateParam(builder, event) {
    this.updated.emit({key: builder, value: event});
  }

  removeParam() {
    this.removed.emit();
    // you need to clear the builders here
  }

}
