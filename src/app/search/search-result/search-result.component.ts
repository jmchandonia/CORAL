import { Component, OnInit, ChangeDetectorRef, AfterViewInit } from '@angular/core';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder } from '../../shared/models/QueryBuilder';
import * as $ from 'jquery';
import 'datatables.net';
import 'datatables.net-bs4';
import { Router, ActivatedRoute } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-search-result',
  templateUrl: './search-result.component.html',
  styleUrls: ['./search-result.component.css']
})
export class SearchResultComponent implements OnInit, AfterViewInit {

  results = [];
  resultFields = [];
  dataTable: any;
  searchQuery: QueryBuilder;
  showQuery = false;
  searchType: string;
  error: any;
  loading = false;
  staticResults = false;
  previousUrl = ['../advanced'];

  constructor(
    private queryBuilder: QueryBuilderService,
    private chRef: ChangeDetectorRef,
    private router: Router,
    private route: ActivatedRoute,
    private spinner: NgxSpinnerService
  ) { }

  ngOnInit() {
    this.loading = true;
    this.searchType = this.queryBuilder.getSearchType();
    this.searchQuery = this.queryBuilder.getCurrentObject();
    this.spinner.show();
    
    this.route.queryParams.subscribe(queryParam => {
      if (queryParam['redirect'] === 'home') {
        this.previousUrl = ['/home']
      }

      if (queryParam['category'] === 'SDT_') {
        this.staticResults = true;
      }
    });
  }

  ngAfterViewInit() {
    this.queryBuilder.getSearchResults()
      .subscribe((res: any) => {
        this.loading = false;
        this.spinner.hide();
        this.results = res.data;
        this.resultFields = res.schema.fields;
        this.chRef.detectChanges();
        const table: any = $('#search-results');
        this.dataTable = table.DataTable({
          autoWidth: false,
        });
      }
    );
  }

  isLink(td: string) {
    return /https?:\/\/.*/.test(td);
  }

  viewData(id) {
    this.router.navigate([`search/result/brick/${id}`]);
  }

  viewCoreData(id) {
    this.router.navigate([`search/result/core/${id}`]);
  }

  useData(id) {
    this.queryBuilder.setPreviousUrl('/search/result');
    this.router.navigate([`../../plot/options/${id}`], {relativeTo: this.route});
  }

}
