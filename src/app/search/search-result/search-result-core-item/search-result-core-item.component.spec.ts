import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchResultCoreItemComponent } from './search-result-core-item.component';

describe('SearchResultCoreItemComponent', () => {
  let component: SearchResultCoreItemComponent;
  let fixture: ComponentFixture<SearchResultCoreItemComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SearchResultCoreItemComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SearchResultCoreItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
