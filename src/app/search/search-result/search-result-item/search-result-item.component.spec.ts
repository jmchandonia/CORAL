import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { SearchResultItemComponent } from './search-result-item.component';
import { ProcessDataComponent } from '../process-data/process-data.component';
import { MockComponent } from 'ng-mocks';
import { HttpClientModule } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { BsModalService, BsModalRef } from 'ngx-bootstrap';
import { ModalModule } from 'ngx-bootstrap/modal';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { ObjectMetadata } from 'src/app/shared/models/object-metadata';

fdescribe('SearchResultItemComponent', () => {

  const mockSearchResult: ObjectMetadata = new ObjectMetadata();
  mockSearchResult.id = 'brickXXXXXXX';
  mockSearchResult.name = 'test_brick_metadata';
  mockSearchResult.description = 'test_brick_description';
  mockSearchResult.array_context.push({
    value_type: {
      oterm_name: 'ENIGMA Campaign',
      oterm_ref: 'ENIGMA:XXXXXXX'
    },
    value: {
      scalar_type: 'oterm_ref',
      value: 'ENIGMA:XXXXXXX'
    }
  });
  mockSearchResult.data_type = {
    oterm_name: 'test_data_type',
    oterm_ref: 'DA:XXXXXXX'
  },
  mockSearchResult.dim_context.push({
    data_type: {
      oterm_name: 'test_data_type',
      oterm_ref: 'DA:XXXXXXX'
    },
    size: 3,
    typed_values: [{
      value_context: [],
      value_type: {
        oterm_name: 'test_value',
        oterm_ref: 'DA:XXXXXXX'
      },
      values: {
        scalar_type: 'string',
        values: ['A', 'B', 'C']
      }
    }]
  });
  mockSearchResult.typed_values.push({
    value_context: [],
    value_type: {
      oterm_name: 'test_value_type',
      oterm_ref: 'ME:XXXXXXX'
    }
  });

  const MockQueryBuilder = {
    getObjectMetadata: () => mockSearchResult
  }



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
      mockProvider(QueryBuilderService, MockQueryBuilder)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });




});
