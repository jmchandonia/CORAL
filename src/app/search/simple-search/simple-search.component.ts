import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryMatch, QueryParam } from '../../shared/models/QueryBuilder';

@Component({
  selector: 'app-simple-search',
  templateUrl: './simple-search.component.html',
  styleUrls: ['./simple-search.component.css']
})
export class SimpleSearchComponent implements OnInit {

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

  private keywordList: Array<Select2OptionData> = [
    {
      id: '0',
      text: 'Microbial'
    },
    {
      id: '1',
      text: 'Biology'
    },
    {
      id: '2',
      text: 'Density'
    },
    {
      id: '3',
      text: 'Genomics'
    }
  ]

  private select2Options = {
    width: '100%',
  }

  private queryMatch: QueryMatch = new QueryMatch();

  private queryBuilderObject: QueryBuilder;

  constructor(
    private queryBuilder: QueryBuilderService
  ) { }

  ngOnInit() {
    this.queryBuilderObject = this.queryBuilder.getCurrentObject();
  }

  updateDataType(event) {
    this.queryMatch.dataType = event.data[0].text;
  }

  updateKeywords(event) {
    this.queryMatch.params = [new QueryParam(null, null, event.data[0].text)];
  }

  submitSearch() {
    console.log('SIMPLE  QBO -> ', JSON.stringify(this.queryMatch));
  }

}
