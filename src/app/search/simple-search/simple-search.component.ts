import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryMatch, QueryParam } from '../../shared/models/QueryBuilder';
import { Router } from '@angular/router';

@Component({
  selector: 'app-simple-search',
  templateUrl: './simple-search.component.html',
  styleUrls: ['./simple-search.component.css']
})
export class SimpleSearchComponent implements OnInit {

  dataModelList: Array<Select2OptionData> = [
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
  ];

  keywordList: Array<Select2OptionData> = [
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
  ];

  select2Options = {
    width: '100%',
  };

  queryMatch: QueryMatch = new QueryMatch();

  queryBuilderObject: QueryBuilder;

  constructor(
    private queryBuilder: QueryBuilderService,
    private router: Router
  ) { }

  ngOnInit() {
    this.queryBuilderObject = this.queryBuilder.getCurrentObject();
  }

  updateDataModel(event) {
    this.queryMatch.dataModel = event.data[0].text;
  }

  updateKeywords(event) {
    this.queryMatch.params = [new QueryParam(null, null, event.data[0].text)];
  }

  onSubmit() {
    console.log('SIMPLE  QBO -> ', JSON.stringify(this.queryMatch));
    this.router.navigate(['/search/result']);
    this.queryBuilder.setSearchType('simple');
  }

}
