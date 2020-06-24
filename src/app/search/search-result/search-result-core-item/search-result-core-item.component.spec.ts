import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { SearchResultCoreItemComponent } from './search-result-core-item.component';
import { ProcessDataComponent } from '../process-data/process-data.component';
import { MockComponent } from 'ng-mocks';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';

describe('SearchResultCoreItemComponent', () => {
  let spectator: Spectator<SearchResultCoreItemComponent>;
  const createComponent = createComponentFactory({
    component: SearchResultCoreItemComponent,
    entryComponents: [
      MockComponent(ProcessDataComponent)
    ],
    imports: [
      RouterModule.forRoot([]),
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
