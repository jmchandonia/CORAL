import { Component, OnInit, Input } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryMatch, QueryParam } from '../../../shared/models/QueryBuilder';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit {


  @Input() queryMatch: QueryMatch;

  private dataTypeList: Array<Select2OptionData> = [
    {
      id: '',
      text: ''
    },
    {
      id: '0',
      text: 'N-dimensional array'
    },
    {
      id: '1',
      text: 'Graph'
    },
    {
      id: '2',
      text: 'Cluster'
    }
  ]

  private propertyParams = [
    {
      type: '',
      match: 'contains',
      keyword: ''
    }
  ]

  constructor() { }

  ngOnInit() {
  }

  updateObjectDataType(event) {
    if (!this.queryMatch) {
      this.queryMatch = new QueryMatch(event.data[0].text);
      // add logic here that will disable propertyParams fields until this is selected
    } else {
      this.queryMatch.dataType = event.data[0].text;
      // here is where we would want to dereference all propertyParams if data type gets updated
    }
    // add some logic here that will call getAttributes http method
  }

  removePropertyParam(param) {
    if (this.propertyParams.length === 1) {
      Object.assign(this.propertyParams[0], {
        type: '',
        match: 'contains',
        keyword: ''
      });
    } else {
      this.propertyParams = this.propertyParams.filter(item => item !== param);
    }
  }

  addPropertyParam(param) {
    this.queryMatch.params.push(param);
  }

}
