import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryMatch, QueryParam } from '../../../shared/models/QueryBuilder';
import { QueryBuilderService } from '../../../shared/services/query-builder.service';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit {

  private queryMatch: QueryMatch = new QueryMatch();
  // make queryMatch input a set function that assigns data value to this.queryMatch
  // @Input() set data(qMatch: QueryMatch) { this.queryMatch = qMatch }
  @Input() connection: string;
  @Output() create: EventEmitter<QueryMatch> = new EventEmitter();


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

  constructor(private queryBuilder: QueryBuilderService) { }

  ngOnInit() {
  }

  updateObjectDataType(event) {
    this.queryMatch.dataType = event.data[0].text;
    // make dropdown for propertyparams disabled until this is selected
    // remove old propertyparam references is a new type is selected
    this.updateQueryMatch();
  }

  updatePropertyParam(index, event) {
    this.queryMatch.params[index][event.key] = event.value.text;
    this.updateQueryMatch();
  }

  removePropertyParam(param) {
    this.queryMatch.params = this.queryMatch.params.filter(p => p !== param);
    this.updateQueryMatch();
  }

  addPropertyParam(param) {
    this.queryMatch.params.push(param);
    this.updateQueryMatch();
  }

  updateQueryMatch() {
    this.queryBuilder.updateQueryMatch(this.connection, this.queryMatch);
  }

}
