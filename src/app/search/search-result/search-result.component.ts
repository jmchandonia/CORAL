import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder } from '../../shared/models/QueryBuilder';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-search-result',
  templateUrl: './search-result.component.html',
  styleUrls: ['./search-result.component.css']
})
export class SearchResultComponent implements OnInit {

  private results = [];
  private resultFields = [];
  private dataTable: any;
  private searchQuery: QueryBuilder;
  private showQuery = false;

  constructor(
    private queryBuilder: QueryBuilderService,
    private chRef: ChangeDetectorRef,
    private router: Router,
    private route: ActivatedRoute
  ) { }

  ngOnInit() {
    this.searchQuery = this.queryBuilder.getCurrentObject();
    this.queryBuilder.getSearchResults()
      .subscribe((res: any) => {
        this.results = res.data;
        this.queryBuilder.resultStore = res.data;
        this.resultFields = res.schema.fields.filter((_, i) => i < 7);
        this.chRef.detectChanges();
        const table: any = $('table');
        this.dataTable = table.DataTable();
      });

    // this.searchQuery = this.queryBuilder.getCurrentObject();
  }

  viewData(id) {
    this.router.navigate([`search/result/${id}`]);
  }

  useData(id) {
    this.router.navigate([`../../plot/options/${id}`], {relativeTo: this.route});
  }

}
