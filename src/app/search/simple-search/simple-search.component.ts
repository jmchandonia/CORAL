import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';

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

  constructor(
    private queryBuilder: QueryBuilderService
  ) { }

  ngOnInit() {
  }

}
