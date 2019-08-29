import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit {

  private dataTypeList: Array<Select2OptionData> = [
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

  addPropertyParam() {
    this.propertyParams.push({
      type: '',
      match: 'contains',
      keyword: ''
    })
  }

}
