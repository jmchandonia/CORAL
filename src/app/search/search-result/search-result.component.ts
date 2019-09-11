import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder } from '../../shared/models/QueryBuilder';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';

@Component({
  selector: 'app-search-result',
  templateUrl: './search-result.component.html',
  styleUrls: ['./search-result.component.css']
})
export class SearchResultComponent implements OnInit {

  private results = [];
  private dataTable: any;
  private searchQuery: QueryBuilder;
  private showQuery = false;

  constructor(
    private queryBuilder: QueryBuilderService,
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.queryBuilder.submitQuery()
      .subscribe(res => console.log('RES', res));

    this.searchQuery = this.queryBuilder.getCurrentObject();
  }

}
