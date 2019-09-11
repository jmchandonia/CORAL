import { Component, OnInit } from '@angular/core';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-search-result-item',
  templateUrl: './search-result-item.component.html',
  styleUrls: ['./search-result-item.component.css']
})
export class SearchResultItemComponent implements OnInit {

  public searchResult: any;

  constructor(
    private qb: QueryBuilderService,
    private route: ActivatedRoute
    ) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      if (params['id']) {
        this.qb.getObjectMetadata(params['id'])
          .subscribe(result => {
            this.searchResult = result;
          });
      }
    });
  }

}
