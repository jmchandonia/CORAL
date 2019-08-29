import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryParam } from '../../../../shared/models/QueryBuilder';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css']
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Output() added: EventEmitter<QueryParam> = new EventEmitter();

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
    this.queryParam = Object.create(param || null);
  }

  constructor() { }

  ngOnInit() {
  }

  addParam() {
    // here we can check for valid data before adding it to our query constructor
    Object.assign(this.queryParam, new QueryParam(
      this.attributeBuilder,
      this.keywordBuilder,
      this.matchTypeBuilder
    ));
    this.added.emit(this.queryParam);
  }

  removeParam() {
    this.removed.emit();
  }

  isEmpty() {
    return Object.keys(this.queryParam).length === 0;
  }

}
