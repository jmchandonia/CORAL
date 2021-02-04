import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { SearchResultItemComponent } from './search-result-item.component';
import { ProcessDataComponent } from '../process-data/process-data.component';
import { MockComponent } from 'ng-mocks';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { ModalModule } from 'ngx-bootstrap/modal';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ObjectMetadata } from 'src/app/shared/models/object-metadata';
const metadata = require('src/app/shared/test/object-metadata.json');
import { Subject } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';

describe('SearchResultItemComponent', () => {

  const mockSearchResultSub = new Subject();

  const mockSearchResult: ObjectMetadata = new ObjectMetadata();
  mockSearchResult.id = 'brickXXXXXXX';
  mockSearchResult.name = 'test_brick_metadata';
  mockSearchResult.description = 'test_brick_description';
  mockSearchResult.array_context = [
];

  const MockQueryBuilder = {
    getObjectMetadata: () => of(metadata)
  };



  let spectator: Spectator<SearchResultItemComponent>;
  const createComponent = createComponentFactory({
    component: SearchResultItemComponent,
    entryComponents: [
      MockComponent(ProcessDataComponent)
    ],
    imports: [
      HttpClientModule,
      RouterModule.forRoot([]),
      ModalModule.forRoot()
    ],
    providers: [
      BsModalService,
      mockProvider(QueryBuilderService, MockQueryBuilder),
      {
        provide: ActivatedRoute,
        useValue: {
          params: of({id: 'brick0000003'})
        }
      },
      {
        provide: Router,
        useValue: { navigate: () => {} }
      }
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should return instance of ObjectMetadata', () => {
    const { searchResult } = spectator.component;
    expect(searchResult).not.toBeUndefined();
  });

  it('should render the correct number of dimensions and variables', () => {
    expect(spectator.queryAll('table')).toHaveLength(4);
    expect(spectator.queryAll('#property-container > tbody > tr')).toHaveLength(3);
    expect(spectator.queryAll('#data-var-container > tbody > tr')).toHaveLength(1);
    expect(spectator.queryAll('#dimension-container > tbody > tr')).toHaveLength(2);
    expect(spectator.queryAll('#attributes-container > tbody > tr')).toHaveLength(2);
  });

  it('should have ProcessDataComponent', () => {
    expect(spectator.query('app-process-data')).not.toBeNull();
  });

  it('should call use for plot method', () => {
    spyOn(spectator.component, 'useForPlot');
    spectator.click('button.btn.btn-secondary');
    expect(spectator.component.useForPlot).toHaveBeenCalled();
  });

});
